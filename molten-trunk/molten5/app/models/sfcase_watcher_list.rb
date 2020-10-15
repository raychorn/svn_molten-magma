class SfcaseWatcherList < ActiveRecord::Base
  sync :with => Case_Watcher_List
  set_primary_key "sf_id"
  
  ###################
  ### Assocations ###
  ###################
  belongs_to :contact,      :class_name => "Sfcontact",
                            :foreign_key => "contact_id__c"
  belongs_to :case_watcher, :class_name => "SfcaseWatcher",
                            :foreign_key => "case_watcher_id__c"
  
  ###################
  ### Validations ###
  ###################
  validates_uniqueness_of :contact_id__c, :scope => [:case_watcher_id__c] 
  
  ########################
  ### Instance Methods ###
  ########################
  
  # Also sets the #email__c attribute (since callbacks don't work)
  def contact=(new_contact)
    write_attribute('contact_id__c', new_contact.id)
    write_attribute('email__c', new_contact.email)
  end
end
