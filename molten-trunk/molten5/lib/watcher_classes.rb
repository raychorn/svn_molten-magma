class Case_Watcher_List < SalesforceRecord
  
  def self.abstract_class?
    false
  end
  
  #################
  ### Behaviors ###
  #################
  set_table_name("Case__Watcher__List") 
  
  ###################
  ### Assocations ###
  ###################
  belongs_to :contact,      :class_name => "Contact",
                            :foreign_key => "contact_id__c"
  belongs_to :case_watcher, :class_name => "Case_Watcher",
                            :foreign_key => "case_watcher_id__c"
  
  ###################
  ### Validations ###
  ###################
  validates_uniqueness_of :contact_id__c, :scope => [:case_watcher_id__c] 
  
  ########################
  ### Instance Methods ###
  ########################
  
  def after_initialize
    self.name = "MOLTEN User" if name.blank?
  end
  
  # Also sets the #email__c attribute (since callbacks don't work)
  def contact=(new_contact)
    write_attribute('contact_id__c', new_contact.id)
    write_attribute('email__c', new_contact.email)
  end
  
  
  ##################################################################
  ### salesforce stuff - if it works, remove and put in a module ###
  ##################################################################
  self.establish_connection :salesforce
  
  @@clone_options = nil
      
  def cloned_class
    AppConstants::CLASS_MAPPINGS[self.class.to_s].constantize
  end

  def self.clone_options
    @@clone_options
  end

  def save_and_clone
    raise("Cloned class not defined via #cloned_class") unless cloned_class
    logger.info("Saving ASF record #{self.class} and getting ready to clone to #{self.cloned_class}")
    if save
      # clone_to_local
      record = SalesforceSync.insert_record(self.class.column_names,self.class.find(self.id),self.class,cloned_class)
      return record
    else
      self
    end
  end
  
  def save_and_update
    raise("Cloned class not defined via #cloned_class") unless cloned_class
    logger.info("Saving ASF record #{self.class} and getting ready to update to #{self.cloned_class}")
    if save
      record = SalesforceSync.update_record(self,cloned_class.find_by_sf_id(id),self.class,cloned_class)
      return record
    end
  end
  
  def clone_exists?
    cloned_class.find_by_sf_id(id)
  end
  alias clone clone_exists?

  def clone_to_local
    klass = cloned_class
    logger.info("Cloning #{self.class} record to #{klass} with attributes: #{attributes}")
    current_time = Time.now
    local = klass.new(attributes.merge({:created_date => current_time,
                                        :system_modstamp => current_time})) 
    local.save
    ActiveRecord::Base.connection.execute("update #{klass.table_name} set sf_id = '#{id}' where id='#{local.id}'")
    return local
  end
end

class Case_Watcher < SalesforceRecord
  #################
  ### Behaviors ###
  #################
  set_table_name("Case__Watcher")
  
  ###################
  ### Assocations ###
  ###################
  # BROKEN IN RAILS 2.0.2 - see #case_watcher_lists
  # has_many    :case_watcher_lists, 
  #             :class_name => "Case_Watcher_List",
  #             :foreign_key => "case_watcher_id__c", :dependent => :destroy
  belongs_to  :support_case, 
              :foreign_key => "case_number_id__c",
              :class_name => 'Case'
  belongs_to  :account, 
              :foreign_key => "account_id__c"
              
  #################
  ### Constants ###
  #################
  
  CASE_FIELDS = "Status; Priority; Comments; Code Streams & Priority; Case Owner; Component; Customer Priority; End Date; Estimated Finish Date; PE Checkpoint; PE Owner; R&D Submission; Requested End Date; Schedule Status; Status 1st Stream; Target Analysis Done; Target Fast Track Build; Target Fix Available; Target Fix Merged; Target Release; Time Stamp / Build"
  
  ##########################
  ### Virtual Attributes ###
  ##########################
  
  # Added to the case_watcher_list as the first contact after create.
  attr_accessor :initial_contact
  
  #################
  ### Callbacks ###
  #################
  
  after_create :add_initial_contact

  ########################
  ### Class Methods ###
  ########################
  
  # If a +CaseWatcher+ exists for the +account+ or +support_case+, then the
  # +contact+ is added to the assocatiated list. 
  # 
  # If a +Case_Watcher+ doesn't exist, then it is created and the given +contact+
  # is added as the first contact. 
  def self.create_subscription!(contact, options)
    if options[:account]
      account = options[:account]
      # case watcher already exists for this account
      if watcher = find_by_account_id__c(account.id)
        # contact isn't subscribing yet to the case watcher
        if !watcher.contacts.include?(contact)
          logger.info "Case Watcher Exists: #{watcher.id}"
           watcher = Case_Watcher_List.create(:contact => contact,:case_watcher => watcher)
           watcher.clone_to_local
        else
          logger.info "Already subscribing"
          true # already subscribing
        end 
      else #case watcher doesn't exist.
        watcher = create(:initial_contact => contact, :account => account, :case_fields__c => CASE_FIELDS)
        watcher.clone_to_local
        logger.info "Created Case Watcher:"
        watcher.attributes.each do |key,value|
          logger.info "#{key}: #{value}"
        end
        list = Case_Watcher_List.create(:contact => watcher.initial_contact,:case_watcher => watcher)
        list.clone_to_local
      end
    # subscribing to a specific support case
    elsif options[:support_case]
      support_case = options[:support_case]
      # case watcher already exists
      if watcher = find_by_case_number_id__c(support_case.id)
        # contact not in subscriber list
        if !watcher.contacts.include?(contact)
           logger.info "Case Watcher Exists: #{watcher.id}"
           list = Case_Watcher_List.create(:contact => contact,:case_watcher => watcher)
           list.clone_to_local
        else
          logger.info "Already subscribing: Watcher [#{watcher.id}] Contact [#{contact.id}]"
          unless local_watcher = watcher.cloned_class.find_by_sf_id(id)
            # for some reason, the local copy doesn't exist...make it
            local_watcher = watcher.clone_to_local
          end
          local_contact = contact.cloned_class.find_by_sf_id(id)
          if !local_watcher.contacts.include?(contact) 
            list = SfcaseWatcherList.create(:contact => contact,:case_watcher => local_watcher)
          end
          true # already subscribing
        end
      # case watcher doesn't exist
      else
        watcher = create(:initial_contact => contact, :support_case => support_case, :case_fields__c => CASE_FIELDS)
        watcher.clone_to_local
        logger.info "Created Case Watcher:"
        watcher.attributes.each do |key,value|
          logger.info "#{key}: #{value}"
        end
        list = Case_Watcher_List.create(:contact => watcher.initial_contact,:case_watcher => watcher)
        list.clone_to_local
      end
    else
      raise "An :account or :support_case must be specified."
    end 
    watcher
  end
  
  # Removes the +contact+ from the case watcher associated with the
  # +account+ or +support_case+.
  def self.remove_subscription!(contact, options)
    if options[:account]
      account = options[:account]
      if watcher = SfcaseWatcher.find_for_contact_and_account(contact.clone)
        watcher.synced_record.unsubscribe!(contact)
      end
    elsif options[:support_case]
      support_case = options[:support_case]
      if watcher = SfcaseWatcher.find_for_contact_and_support_case(contact.clone, support_case.clone)
        if watcher.synced_record
          watcher.synced_record.unsubscribe!(contact)
        else
          # couldn't find sf record...delete local sub
          watcher.destroy
        end
      end
    else
      raise "Please specify an :account or :support_case"
    end
  end
  
  ########################
  ### Instance Methods ###
  ########################
  
  # Unsubscribes the +contact+ from this CaseWatcher.
  # Also destroys this CaseWatcher if the subscriber list is now empty.
  def unsubscribe!(contact)
    # try to find the contact in the case watcher list
    subscriber = Case_Watcher_List.find(:first, :conditions => ["case_watcher_id__c = ? AND contact_id__c = ?",id,contact.id])
    # if the contact is in the subscriber list, delete the SF record and the local copy
    if subscriber
      subscriber.class.establish_connection :salesforce
      subscriber.destroy 
      subscriber.clone.destroy if subscriber.clone
    elsif local_watcher = SfcaseWatcherList.find(:first, :conditions => ["case_watcher_id__c = ? AND contact_id__c = ?",id,contact.id])
    # couldn't find the SF record...delete the local one
      local_watcher.destroy
    end
    # if the subscriber list is empty, delete the case watcher as well
    if case_watcher_lists.empty?
      Case_Watcher_List.destroy(id)
      clone.destroy if clone
    end
  end
  
  def case_watcher_lists(extra_conditions = nil)
    Case_Watcher_List.find(:all, :conditions => ["case_watcher_id__c = ? #{extra_conditions ? 'AND ' + extra_conditions : ''}",id])
  end
  
  def contacts
    return [] unless case_watcher_lists.any?
    case_watcher_lists.map(&:contact)
  end
  
  ##################################################################
  ### salesforce stuff - if it works, remove and put in a module ###
  ##################################################################
  self.establish_connection :salesforce
  
  @@clone_options = nil
      
  def cloned_class
    AppConstants::CLASS_MAPPINGS[self.class.to_s].constantize
  end

  def self.clone_options
    @@clone_options
  end

  def save_and_clone
    raise("Cloned class not defined via #cloned_class") unless cloned_class
    logger.info("Saving ASF record #{self.class} and getting ready to clone to #{self.cloned_class}")
    if save
      # clone_to_local
      record = SalesforceSync.insert_record(self.class.column_names,self.class.find(self.id),self.class,cloned_class)
      return record
    else
      self
    end
  end
  
  def save_and_update
    raise("Cloned class not defined via #cloned_class") unless cloned_class
    logger.info("Saving ASF record #{self.class} and getting ready to update to #{self.cloned_class}")
    if save
      record = SalesforceSync.update_record(self,cloned_class.find_by_sf_id(id),self.class,cloned_class)
      return record
    end
  end
  
  def clone_exists?
    cloned_class.find_by_sf_id(id)
  end
  alias clone clone_exists?

  def clone_to_local
    klass = cloned_class
    logger.info("Cloning #{self.class} record to #{klass} with attributes: #{attributes}")
    current_time = Time.now
    local = klass.new(attributes.merge({:created_date => current_time,
                                        :system_modstamp => current_time})) 
    local.save
    ActiveRecord::Base.connection.execute("update #{klass.table_name} set sf_id = '#{id}' where id='#{local.id}'")
    return local
  end
  
  private
  
  # Adds the +initial_contact+ after_create.
  def add_initial_contact
    # case_watcher_lists.create(:contact => initial_contact)
  end
end