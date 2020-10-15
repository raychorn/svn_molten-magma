require_dependency 'authentication_system/contact_methods'
require 'digest/md5'

class Sfcontact < ActiveRecord::Base
  #################
  ### Behaviors ###
  #################
  sync :with => Contact
  include AuthenticationSystem::ContactMethods
  set_primary_key "sf_id"
  serialize :account_filter_ids_array
  
  ###################
  ### Assocations ###
  ###################
  belongs_to :company, :class_name => "Sfaccount", :foreign_key => "account_id"
  alias_method :account, :company
  has_many :cases, :class_name => "Sfcase", :foreign_key => "contact_id", 
           :order => "last_modified_date DESC"
  has_many :attachments, :through => :cases
  has_one :settings, :class_name => "SfcontactSetting", :foreign_key => "sfcontact_id"
  has_many :viewings, :order => "created_at DESC"
  has_one :sfssl, :foreign_key => "contact_id"
  has_one :sfuser, :foreign_key => "user_contact_id__c"
  has_many :contacts, :through => :sfuser
  has_many :accounts_subscriptions, :class_name => "SfcaseWatcherList", 
           :foreign_key => "contact_id__c", :include => [:case_watcher],
           :conditions => "sfcase_watcher.account_id__c IS NOT NULL"
  has_many :cases_subscriptions, :class_name => "SfcaseWatcherList", 
           :foreign_key => "contact_id__c", :include => [:case_watcher],
           :conditions => "sfcase_watcher.case_number_id__c IS NOT NULL"
  belongs_to :last_read_marketing_message, :class_name => 'SfmoltenPost', :foreign_key => 'last_read_marketing_message_id'
           
  ###################
  ### Validations ###
  ###################
  validates_presence_of :email, :on => :create
  
  #################
  ### Callbacks ###
  #################
  before_create :generate_token
  after_save :initialize_settings
  
  #################
  ### Constants ###
  #################
  
  CUSTOM_HOME_PAGE_RECORD_TYPE = "012300000001OPDAA2"
  
  ##########################
  ### Virtual Attributes ###
  ##########################
  
  attr_accessor :last_seen_at
  
  #####################
  ### Class Methods ###
  #####################
  
  # SHOULD BE UPDATE_AND_SYNC...BUT HAVING SF PROBLEM WITH DATES
  # Resets the +portal_last_confirm_date__c+ for all users
  def self.reset_last_confirm_date(date = Time.now)
    Sfcontact.find(:all).each do |c| 
      c.update_attributes({:portal_last_confirm_date__c => date, :portal_last_confirm_sent_date__c => date} ) 
    end
  end
  
  # Sends emails to all users who have not confirmed their account within the past +AppConstants::CONFIRMATION_RANGE+.
  # If a user has already been sent a confirmation and it was sent between the deadline and the range, then they are not sent
  # another confirmation. 
  #
  # Only active users are sent confirmations.
  #
  # THIS SHOULD BE SCHEDULED TO RUN DAILY VIA A CRON JOB
  def self.send_confirmations(options = {})
    contacts = find(:all, 
                   {:conditions => ["portal_last_confirm_date__c < ? AND portal_last_confirm_sent_date__c < ? AND contact_status__c = ?",
                   AppConstants::CONFIRMATION_RANGE, AppConstants::CONFIRMATION_RANGE_LIMIT,'Active']}.merge(options)).each do |c|
                     if c.synced_record.nil? or c.synced_record.password_reset_sent_at__c.nil? or c.synced_record.password_reset_sent_at__c < AppConstants::CONFIRMATION_RANGE
                       Sfcontact.transaction do
                         begin
                           #SfcontactMailer.deliver_confirmation(c)
                         rescue Exception => e
                           logger.info("error sending confirm email to: #{c.email} / #{e}")
                         end
                         c.update_attribute('portal_last_confirm_sent_date__c',Time.now)
                         begin
                           if s = Contact.find(:first, :conditions => "id = '#{c.sf_id}'")
                            #s.password_reset_sent_at__c = Time.now.strftime("%Y-%m-%dT%H:%M:%SZ")
                            #s.save!
                           else
                             logger.info("Couldn't find associated contact with id: #{c.sf_id} for #{c.email}")
                           end
                         # id may not be well-formed
                         rescue ActiveSalesforce::ASFError
                            logger.info("Couldn't find associated contact with id: #{c.sf_id} for #{c.email}")
                         end
                         logger.info("Sent password reset email to: #{c.email} and updated the SF resent time to: #{s.password_reset_sent_at__c if c.synced_record}")
                       end  
                     else
                         logger.info("A password reset email has already been sent to: #{c.email} within the current time range #{c.synced_record.password_reset_sent_at__c}")
                     end                
                   end
    return contacts;
  end
  
  # Marks the account with +id+ and +token+ as confirmed.
  def self.confirm(id,token)  
    if contact = Sfcontact.find(:first, :include => [:settings], 
                     :conditions => ["sf_id = ? AND sfcontact_setting.token = ? and contact_status__c = ?", id,token,"Active"])
      contact.confirm!
      return contact
    else
      logger.info("Failed to confirm contact with id [#{id}] and token [#{token}]")
      return nil
    end
  end
  
  def self.deactivate_unconfirmed
    contacts = find(:all, 
                   :conditions => ["portal_last_confirm_date__c < ? AND contact_status__c = ?",
                   AppConstants::CONFIRMATION_RANGE_LIMIT,'Active']).each do |c|
                     Sfcontact.transaction do
                       c.deactivate!
                     end                     
                   end
    return contacts;
  end
  
  # SHOULD ALS UPDATE THE SF TIME
  # Marks the account as 'Inactive'
  def deactivate!
    update_attribute('contact_status__c','Inactive')
  end
  
  # SHOULD ALSO UPDATE SF TIME
  # Updates the confirmation time for this contact.
  def confirm!
    update_attribute('portal_last_confirm_date__c', Time.now)
    settings.update_attribute('token',generate_token)
  end
  
  ########################
  ### Instance Methods ###
  ########################

  # Finds the custom home page available to this user. If none is found, nil is returned. 
  def custom_home_page
    page = get_home_page(company)
    if page.nil? and company.ancestors.any?
      company.ancestors.each do |c|
        page = get_home_page(c)
        if page then return page end
      end
    end
    return page
  end
  
  def get_home_page(account)
    Sfsolution.find(:first,
                    :order => "last_modified_date DESC",
                    :conditions => ["record_type_id = ? AND portal_account_name_id__c = ?",CUSTOM_HOME_PAGE_RECORD_TYPE,account.id] )
  end
  
  ### Beast Methods ###
  
  def forum_name
    if forum_setting
      forum_setting.name
    else
      name
    end
  end
  
  def moderator_of?(forum)
    moderatorships.count(:all, :conditions => ['forum_id = ?', (forum.is_a?(Forum) ? forum.id : forum)]) == 1
  end
  
  ### End Beast Methods ###
  
  ### Beast Methods ###
  
  def forum_name
    if forum_setting
      forum_setting.name
    else
      name
    end
  end
  
  def moderator_of?(forum)
    moderatorships.count(:all, :conditions => ['forum_id = ?', (forum.is_a?(Forum) ? forum.id : forum)]) == 1
  end
  
  ### End Beast Methods ###
  
  # Returns true if the user has access to the 'share cases' area for the 
  # +account+.
  def share_cases?(account)
    if [AppConstants::PRIVILEGE[:super_user],AppConstants::PRIVILEGE[:admin],AppConstants::PRIVILEGE[:user_manager]].include?(portal_privilege) and account == company
      true
    else
      false
    end
  end
  
  # True if the user is a User Manager or greater
  def forum_admin?
    privilege?('User Manager')
  end
  
  # Determines if the contact has the specified privileges. 
  # Privileges (from lowest to highest):
  #   - Member
  #   - Super User
  #   - User Manager
  #   - Support Admin
  #   - Admin
  def privilege?(privilege_type)
    admin_chain = AppConstants::PRIVILEGE.values.reject { |p| p == AppConstants::PRIVILEGE[:inactive] }
    support_admin_chain = admin_chain.reject { |p| p == AppConstants::PRIVILEGE[:admin] }
    super_user_chain = support_admin_chain.reject do |p|
      [ AppConstants::PRIVILEGE[:marketing_admin], 
        AppConstants::PRIVILEGE[:support_admin], 
      ].include?(p)
    end
    member_chain = super_user_chain.reject { |p| p == AppConstants::PRIVILEGE[:super_user] }
    
    case portal_privilege
    when AppConstants::PRIVILEGE[:admin]
      admin_chain.include?(privilege_type)
    when AppConstants::PRIVILEGE[:support_admin]
      support_admin_chain.include?(privilege_type)
    when AppConstants::PRIVILEGE[:user_manager]
      super_user_chain.include?(privilege_type)
    when AppConstants::PRIVILEGE[:super_user]
      super_user_chain.include?(privilege_type)
    when AppConstants::PRIVILEGE[:member]
      member_chain.include?(privilege_type)
    end
  end
  
  # True if the user has access to file downloads.
  def file_download_access?
    if license_delivery_contact == 'Yes'
      true
    end
  end
  
  # Returns +true+ if cases of +status+ are viewable on the Support Cases List view.
  def case_viewable?(status)
    retrieve_case(status).viewable? if settings
  end
  
  # TODO - RENAME TO set_status_filters
  # Takes an array of case status to mark as viewable. 
  # Any case statuses not in the array are marked as not-viewable. 
  #
  # If +status_array+ is nil, then returns currently viewable statuses.
  def set_case_filters(status_array = nil)
    if status_array.nil?
      status = Array.new
      AppConstants::CASE_SORT_ORDER.each do |s|
        if retrieve_case(s).viewable == true
          status << s
        end
      end
      return status
    else
      status_array.each do |status|
        retrieve_case(status).update_attribute(:viewable, true)
      end
      (AppConstants::CASE_SORT_ORDER - status_array).each do |status|
        retrieve_case(status).update_attribute(:viewable, false)
      end
      return status_array
    end
  end
  
  # Takes an array of Accounts to mark as viewable in the cases/list view.
  # If +account_filter_ids_array+ is nil, then returns +company+ plus its children.
  def set_account_filters(account_array = nil)
    if account_array.nil?
      return account_filters
    else
      self.account_filter_ids_array = account_array
      save
      return account_filters
    end
  end
  
  def account_filters
    if account_filter_ids_array.is_a?(Array) and account_filter_ids_array.any?
      Sfaccount.find(account_filter_ids_array)
    else
      [company] + company.children
    end
  end
  
  def toggle_case_viewable(status)
    retrieve_case(status).toggle!('viewable')
  end
  
  def retrieve_case(status)
    settings.case_view(status)
  end

  # combines the user's first and last name
  def name
    value = "#{last_name}, #{first_name}".strip
    if value == ','
      ''
    else
      value
    end
  end
  alias to_s name
  
  def first_and_last
    "#{first_name} #{last_name}".strip
  end
   
  def recently_updated_cases(*args)
    cases.find(:all, :limit => AppConstants::RECENTLY_UPDATED_LIMIT,
               :order => "last_modified_date DESC")
  end
  
  def recently_viewed_solutions
    Sfsolution.find_new
  end
  
  # Returns an Array of +Sfaccount+ records that this contact is
  # associated with.
  def account_list
    return [] unless company
    [company] + company.sibling_accounts
  end
  
  # Returns a 2D-Array with cases grouped by status ordered by AppConstants::CASE_SORT_ORDER.
  #
  # Cases can be sorted within their status groups by passing an optional +sort+ and +order+ param.
  #   - sort: column to sort by
  #           default: 'last_modified_date'
  #   - order: Ordering of results
  #           default: 'DESC'
  #   - all_at_company: Grab all cases at this company (not just for this contact)
  #
  # Example: #cases_grouped_by_status(:sort => 'component', :order => 'ASC')
  def cases_grouped_by_status(options = {}) 
    options.delete_if { |key,value| value.blank? }
    options = {:sort => 'sfcase.last_modified_date', :order => 'DESC', :all_at_company => false}.merge(options)
    sort_sql = options[:sort] + ' ' + options[:order]
    
    if options[:all_at_company] and company
      # owner sort is handled thru Ruby...could be 
      # either a Sfgroup or a Sfuser
      if options[:sort] == 'sfuser.last_name'
        cases = Sfcase.find(:all, :include => [:contact], 
        :conditions => ["sfcase.contact_id IN (?)",company.associated_contacts.map { |c| c.id  }])
        cases = sort_cases_by_owner(cases,options)
      else 
        cases = Sfcase.find(:all, :include => [:contact], 
        :conditions => ["sfcase.contact_id IN (?)",company.associated_contacts.map { |c| c.id  }], 
        :order => sort_sql).group_by(&:status)
      end
    else
      if options[:sort] == 'sfuser.last_name'
        cases = Sfcase.find(:all, 
        :include => [:contact], 
        :conditions => "sfcase.contact_id = '#{id}'")
        cases = sort_cases_by_owner(cases,options)
      else
        cases = Sfcase.find(:all, 
        :include => [:contact], 
        :conditions => "sfcase.contact_id = '#{id}'", 
        :order => sort_sql).group_by(&:status)
      end
    end
    # cases = self.cases.find(:all, :order => sort_sql ).group_by(&:status)
    # cases = cases.group_by(&:status)
    ordered_cases = []
    AppConstants::CASE_SORT_ORDER.each do |status|
      cases.keys.each do |key|
        if key == status
          ordered_cases << [key,cases[key]]
          cases.delete(key)
        end
      end
    end
    # add in cases that aren't of any of the specified groups
    ordered_cases
    # now add in other case statuses
    cases.keys.each do |key|
      ordered_cases << [key, cases[key]]
    end
    ordered_cases
  end
  
  def sort_cases_by_owner(cases,options)
    if options[:order] == 'ASC'
      cases.sort! { |x,y| x.owner.sort_name <=> y.owner.sort_name }
    else
      cases.sort! { |x,y| y.owner.sort_name <=> x.owner.sort_name }
    end
    cases = cases.group_by(&:status)
  end
  
  # 
  # This provides #recent_class_name style methods that return a list of the
  # recently viewed viewables of that class type:
  # 
  #   current_user.recent_sfcases  #=> [Sfcase, Sfcase, ...]
  # 
  def method_missing(meth, *args, &block)
    if meth.to_s =~ /^recent_(\w+)$/
      recent_type = $1.singularize.camelize.constantize
      views = viewings.find(:all, :limit => AppConstants::RECENT_LIMIT, :order => "created_at DESC",
                    :conditions => "viewable_type = '#{recent_type}'").map { |viewing| viewing.viewable  }.uniq.compact
      # make sure the viewings are available to this contact
      views.reject { |v| !v.account.blank? and !account_list.include?(v.account) }
    else
      super
    end
  end
  
  # Sends a welcome email to the contact if they are a new contact.
  # If the email has already been sent, then the welcome email is not sent. 
  def send_welcome_email(sf_record_id)
    if contact = Contact.find(sf_record_id)
      # only send if (a) the welcome email hasn't been sent and (b) the contact has an associated self service user and that user is active
      if !contact.welcome_email_sent? and (self_service = SelfServiceUser.find_by_contact_id(sf_record_id) and self_service.is_active)
        contact.update_attribute('welcome_email_sent_at__c',Time.now)
        SfcontactMailer.deliver_welcome(self,contact,self_service.email)
        logger.info("Updating contact with id: #{contact.id}")
        logger.info("Contact Email Sent Time Updated: #{contact.welcome_email_sent_at__c}")
      else
        logger.info("Welcome email already sent to contact: #{self.email}")
      end
    else
      logger.info("Couldn't find associated contact: #{self.email}")
    end
  end
  
  # Returns the contact's saved case views
  def case_reports(options = {})
    CaseReport.find(:all, {:conditions => ["contact_id = ? OR (account_id = ? AND shared = TRUE)", id, account_id], :order => 'updated_at DESC'}.merge(options))
  end
  alias_method :saved_case_reports, :case_reports
  
  def owned_case_reports(options = {})
    CaseReport.find(:all, {:conditions => ["contact_id = ?", id], :order => 'updated_at DESC'}.merge(options))
  end
  
  private
  
  # create local settings unless it already exists.
  def initialize_settings
    create_settings unless SfcontactSetting.find_by_sfcontact_id("#{sf_id}")
  end
end