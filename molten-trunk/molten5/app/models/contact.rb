class Contact < SalesforceRecord
  # cloned_class :sfcontact
  establish_connection :salesforce
  set_primary_key "id"
  
  # combines the user's first and last name
  def name
    "#{first_name} #{last_name}".strip
  end
  
  def welcome_email_sent?
    welcome_email_sent_at__c
  end
  
end
