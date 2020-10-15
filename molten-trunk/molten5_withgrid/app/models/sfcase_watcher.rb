class SfcaseWatcher < ActiveRecord::Base
  #------------------
  # BEHAVIORS
  #------------------
  sync :with => Case_Watcher
  set_primary_key "sf_id"
  
  ####################
  ### Associations ###
  ####################
  has_many    :case_watcher_lists, 
              :class_name => "SfcaseWatcherList",
              :foreign_key => "case_watcher_id__c"
  belongs_to  :support_case, 
              :foreign_key => "case_number_id__c",
              :class_name => 'Sfcase'
  belongs_to  :account, 
              :foreign_key => "account_id__c",
              :class_name => 'Sfaccount'

  #################
  ### Constants ###
  #################

  #####################
  ### Class Methods ###
  #####################
  
  # Returns a SFcaseWatcher record if the +contact+ is subscribing to
  # a CaseWatcher for their associated account.
  def self.find_for_contact_and_account(contact)
    if contact and (watcher_for_account = find_by_account_id__c(contact.account_id)) 
        if watcher_for_account.contacts.include?(contact)
           watcher_for_account
        else
          nil # watcher for account exists, but contact isn't subscribing.
        end
    else
      nil
    end
  end
  
  # Returns a SFcaseWatcher record if the +contact+ is subscribing to
  # a SFcaseWatcher for the given +support_case+.
  def self.find_for_contact_and_support_case(contact,support_case)
    if watcher_for_case = find_by_case_number_id__c(support_case.id)
        if watcher_for_case.contacts.include?(contact)
           watcher_for_case
        else
          nil # watcher for case exists, but contact isn't subscribing.
        end
    else
      nil
    end
  end

  ########################
  ### Instance Methods ###
  ########################
  
  def contacts
    return [] unless case_watcher_lists.any?
    case_watcher_lists.map(&:contact).compact
  end

end