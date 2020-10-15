class User < SalesforceRecord
  set_primary_key "id"
  # cloned_class :sfuser
  
  # combines the user's first and last name
  def name
    "#{first_name} #{last_name}".strip
  end
end
