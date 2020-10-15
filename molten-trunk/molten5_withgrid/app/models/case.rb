class Case < SalesforceRecord
  establish_connection :salesforce
  # cloned_class :sfcase
  set_primary_key "id"
  set_table_name 'case'
end
