class Sfcase < ActiveRecord::Base
  #################
  ### Constants ###
  #################
  CLOSED_STATES = [
                    "Closed",'Closed',
                    'Closed Duplicate',
                    "Closed Fixed by Subsequent Change",
                    "Closed Not a Problem",
                    "Closed User Error",
                    "Closed Will Not Fix"
  ]
  
  RATINGS = [  
    'Excellent',
    'Very Good',
    'Good',
    'Poor'
  ]
  
  # These attributes are editable for existing cases through the #edit form. 
  EDITABLE_ATTRIBUTES = %w(customer_priority__c expected_resolution_date__c customer_tracking__c description weekly_notes__c tag__c)
  
  FERRET_CUSTOM_FIELDS = {:contact_account_id => {},:contact_name => {}, :comments_text => {}, :owner_name => {},
                          :attachment_names => {}}.reject { |k,v| AppConstants::IGNORE_FIELDS.include?(k.to_sym)}
                          
  
  #################
  ### Behaviors ###
  #################
  include Cachable
  sync :with => Case
  set_primary_key "sf_id"
  acts_as_viewable
  acts_as_ferret( { :fields =>
    {
       :sf_id              => {},
       :case_number        => {},
       :supplied_name      => {},
       :supplied_email     => {},
       :supplied_phone     => {},
       :supplied_company   => {},
       :subject            => {:boost => 3},
       :priority           => {},
       :description        => {},
       :query_build_view__c => {},
       :weekly_notes__c => {},
       :tag__c => {}
     }.merge(FERRET_CUSTOM_FIELDS), :remote => true } )
  
  #------------------
  # ASSOCIATIONS
  #------------------
  belongs_to :contact, :class_name => "Sfcontact", :foreign_key => "contact_id"
  belongs_to :last_modified_by, :class_name => "Sfuser", :foreign_key => "last_modified_by_id"
  has_many :comments, :class_name => "Sfccomment", :foreign_key => "parent_id", :order => "created_date DESC", 
                      :conditions => "is_published = '1'"
  has_many :attachments, :class_name => "Sfattach", :foreign_key => "parent_id"
  # belongs_to :owner, :class_name => "Sfuser", :foreign_key => "owner_id"
  has_one :watcher,   :class_name => 'SfcaseWatcher',
                      :foreign_key => 'case_number_id__c'
  belongs_to :account, :class_name => "Sfaccount", :foreign_key => "account_id"
  
  def owner
    if user = Sfuser.find_by_sf_id(owner_id)
      user
    elsif group = Sfgroup.find_by_sf_id(owner_id)
      group
    end
  end
  
  #------------------
  # VALIDATIONS
  #------------------
  validates_presence_of :subject, :sf_type, :customer_priority__c, :description, :operating_system__c, :product__c,
                        :component__c, :query_build_view__c, :version_number__c, :on => :create, 
                        :if => Proc.new { |support_case| support_case.validate_case_attributes }
  # validates_presence_of :sf_id, :on => :create, :if => Proc.new { |support_case| !support_case.validate_case_attributes }

  #------------------
  # VIRTUAL ATTRIBUTES
  #------------------
  attr_accessor :validate_case_attributes
  
  #################
  ### Callbacks ###
  #################
  
  before_save :set_update_time
  
  #####################
  ### Class Methods ###
  #####################
  
  def self.full_text_search(q,contact,options = {})
    return [0,[]] if q.nil? or q=="" or contact.nil?
    query = q.dup
    
    default_options = {:limit => AppConstants::SOLUTIONS_PER_PAGE, :page => 1,:field => nil}  
    options = default_options.merge options
    
    # add the field restriction
    field = options[:field].to_s
    query = field.blank? ? query : field + ':' + query
    
    # handle pagination
    options[:offset] = options[:limit] * (page = options.delete(:page).to_i and page > 0 ? page-1 : 0)
    
    # limit to account-specific cases
    query = query + " +contact_account_id:("
    account_list = contact.account_list.map do |a| 
       a.id 
    end.join(' OR ')
    query += account_list + ') '
    
    logger.info 'the query: '
    logger.info query
    
    results = find_by_contents(query, options)
    
    [results.total_hits, results]
  end
  
  #------------------
  # INSTANCE METHODS
  #------------------
  
  # True if:
  # - the +c+ is the case's associated #contact.
  # - the +c+ has AppConstants::PRIVILEGE[:super_user] privileges at the 
  #   #contact's company. 
  # Use this to determine if a case is editable by the +c+.
  def actionable?(c = nil)
    return unless c
    if c == contact 
      true
    elsif c.privilege?(AppConstants::PRIVILEGE[:super_user]) and c.company == contact.company
      true
    else
      false
    end
  end
  
  # Needs to be dynamic
  def aging_weeks__c
    if %w(1 true).include?(is_closed.to_s.downcase)
      (last_modified_date.to_i-created_date.to_i)/(60*60*24*7)
    else
      (Time.now.to_i - created_date.to_i)/(60*60*24*7)
    end
  end
  
  def after_initialize
    self.customer_priority__c = "3 - Med" unless self.customer_priority__c
  end
  
  def closed?
    CLOSED_STATES.include?(status)
  end
  
  # Removes the 3 leading zeros from the case number. 
  def stripped_case_number
    return unless case_number
    case_number.to_s.gsub(/^000/,'')
  end
  
  # Closes the case. Requires a status. 
  # Options:
  # - comment
  # - rating
  def close!(state, contact, options = {})
    raise "Please provide a state for the case." if state.blank?
    update_attributes_and_sync(:status => state, :mode__c => options[:rating])
    if !options[:comment].blank?
      comment = CaseComment.new(:parent => self.synced_record, :comment_body => options[:comment], 
                                :created_by => contact,
                                :is_published => '1')                                    
      unless comment = comment.save_and_clone
        logger.info("An error occurred add comment")
        raise "The comment could not be saved: #{comment.errors.full_messages.join(', ')}"
      end # unless
    end # comment.blank
  end # close!
  
  # Sets the +last_updated+ time. Note that the record IS NOT SAVED. 
  # Accepts an optional parameter - the time to set as the +last_updated+ time. Otherwise,
  # the case's own +last_modified_date+ is used.
  def set_update_time(time = last_modified_date)
    self.last_updated__c = ((last_updated__c and time < last_updated__c) ? last_updated__c : time) # fails migration ?
#    self.last_updated__c = self.last_modified_date      # for migration
  end
   
   # Sets the +last+updated+ time and saves the support case, skipping the ferret update. 
  def set_update_time!(time = last_modified_date)
    set_update_time(time)
    # disable_ferret
    save
    return last_updated__c
  end
  
  #### Ferret Custom Attributes
    
  def contact_name
    contact.name if contact
  end
  
  def contact_account_id
    contact.account_id if contact
  end
  
  def comments_text
    comments.map(&:comment_body).join(' ')
  end
  
  def attachment_names
    attachments.map(&:name).join(' ')
  end
  
  def owner_name
    if owner.is_a?(String)
      owner
    elsif !owner.nil?
      owner.name
    end
  end
end
