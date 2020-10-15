class Sfaccount < ActiveRecord::Base
  sync :with => Account
  set_primary_key "sf_id"
  acts_as_tree
  
  #################
  ### Constants ###
  #################
  
  SCOPES = {
    :children_accounts => "View all children Accounts",
    :this_account => "View this Account only"
  }
  
  ####################
  ### Associations ###
  ####################
  has_many :contacts, :class_name => 'Sfcontact', :foreign_key => 'account_id',
                      :conditions => "contact_status__c = 'Active'"
  has_one :watcher,   :class_name => 'SfcaseWatcher',
                      :foreign_key => 'account_id__c'
  has_many :cases,    :class_name => 'Sfcase',
                      :foreign_key => "account_id"

  ########################
  ### Instance Methods ###
  ########################

  # Grabs all contacts associated with this account and
  # the rest of the contacts in the scope. 
  # Logic:
  # * If +portal_case_scope__c+ is +SCOPE[:this_account]+, grab
  #   just the contacts associated with this account. 
  # * If +portal_case_scope__c+ is +SCOPE[:children_accounts]+, grab this
  #   this account's contacts plus the contacts of its child accounts.
  # * If +portal_case_scope__c+ is empty and there is a parent, defer to the parent of this account. 
  # * If +portal_case_scope__c+ is empty and there is NOT a parent, then grab just its
  #   associated contacts.
  # * If +portal_case_scope__c+ is empty and the root account's +portal_case_scope__c+ is also empty,
  #   then grab just those contacts directly associated with this account (and NOT those with the ancestor accounts).
  def associated_contacts(accounts_path = [])
    if portal_case_scope__c == SCOPES[:this_account]
      contacts
    elsif portal_case_scope__c == SCOPES[:children_accounts]
      self.contacts + sibling_contacts
    elsif portal_case_scope__c.nil? and parent
      parent.associated_contacts(accounts_path << self)
    else # portal_case_scope__c is nil and this is root
      if accounts_path.empty?
        contacts
      else
        accounts_path.first.contacts
      end
    end
  end

  # Query doesn't work in ASF for siblings.
  def sibling_accounts
    Sfaccount.find(:all, :conditions => ["parent_id = ?",id])
  end
  
  # Returns ancestors, siblings, children, and this account.
  def all_in_tree
    accounts = Array.new
    accounts += ancestors
    accounts += sibling_accounts
    accounts += children
    accounts << self
    return accounts
  end

  def sibling_contacts
    Sfcontact.find(:all, :conditions => ["account_id IN (?) AND contact_status__c = 'Active'",sibling_accounts.map(&:id)])
    # sibling_accounts.map(&:contacts).flatten
  end
end
