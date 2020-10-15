class CaseColumnsSetting < ActiveRecord::Base
  #################
  ### Behaviors ###
  #################
  set_primary_key "id"
  
  ###################
  ### Assocations ###
  ###################
  belongs_to :sfcontact_setting
  
  ###################
  ### Validations ###
  ###################
  validates_uniqueness_of :sfcontact_setting_id
  
  #################
  ### Constants ###
  #################
  
  YOUR_CASE_COLUMNS = [
    {:col => 'component__c', :desc => 'Component', :default => true, :meth => "component" },
    {:col => 'sfuser___last_name', :desc => 'Owner', :default => true, :meth => "owner"},
    {:col => 'sf_type', :desc => 'Type', :default => true, :meth => "sf_type" },
    {:col => 'customer_priority__c', :desc => 'Priority', :default => true, :meth => "customer_priority__c" },
    {:col => 'sfcase___created_date', :desc => 'Opened', :default => true, :meth => "created_date.strftime(\"%m/%d/%y\") if support_case.created_date" },
    {:col => 'sfcase___last_updated__c', :desc => 'Updated', :default => true, :meth => "last_updated__c.strftime(\"%m/%d/%y\") if support_case.last_updated__c" },
    {:col => 'sfcontact___last_name', :desc => 'Contact Name', :default => false, :meth => "contact" },
    {:col => 'expected_resolution_date__c', :desc => 'Need by Date', :default => false, :meth => "expected_resolution_date__c.strftime(\"%m/%d/%y\") if support_case.expected_resolution_date__c" },
    {:col => 'cr_status__c', :desc => 'CR Status', :default => false, :meth => "cr_status__c" },
    {:col => 'cr_number__c', :desc => 'CR Number', :default => false, :meth => "cr_number__c" },
    {:col => 'expedited_priority__c', :desc => 'Expedited Priority', :default => false, :meth => "expedited_priority__c" },
    {:col => 'customer_priority__c', :desc => 'Customer Priority', :default => false, :meth => "customer_priority__c" },
    # {:col => 'contact_id', :desc => 'Contact Name', :default => false, :meth => "Sfcontact.find('#{contact_id}').name" },
    {:col => 'customer_tracking__c', :desc => 'Customer Tracking #', :default => false, :meth => "customer_tracking__c" },
    {:col => 'weekly_notes__c', :desc => 'Weekly Notes', :default => false, :meth => "weekly_notes__c" },
    {:col => 'tag__c', :desc => 'Tag', :default => false, :meth => "tag__c" },
    {:col => 'account', :desc => 'Account', :default => false, :meth => "account.name if support_case.account" },
    {:col => 'expected_build_date__c', :desc => 'Expected Build Date', :default => false, :meth => "expected_build_date__c.strftime(\"%m/%d/%y\") if support_case.expected_build_date__c" },
  ]
  
  ALL_CASE_COLUMNS = YOUR_CASE_COLUMNS
  
  MIN_COUNT = 4
  MAX_COUNT = 6
  
  ###################
  ### Validations ###
  ###################
  
  # validate_on_update :all_attributes_valid
  #   validate_on_update :your_attributes_valid
  
  def your_attributes_valid
    do_validate_attributes('your')
  end
  
  def all_attributes_valid
    do_validate_attributes('all')
  end
  
  def do_validate_attributes(type)
    count = send("#{type}_attributes").select { |key,value| value == true }.size
    if count < MIN_COUNT or count > MAX_COUNT 
      errors.add_to_base("You must select between #{MIN_COUNT} and #{MAX_COUNT} columns to display when viewing <strong>#{type} cases</strong>. You've selected #{count}.")
    end
  end
  
  ########################
  ### Instance Methods ###
  ########################
  
  def your_attributes
    attributes.select { |key,value| key =~ /your/ }
  end
  
  def all_attributes
    attributes.select { |key,value| key =~ /all/ }
  end
  
  def your_case_columns
    cols = YOUR_CASE_COLUMNS.dup
    cols.each do |col|
      col.merge!({:attr => 'your_'+col[:col], :value => send('your_'+col[:col]), :sort => col[:col].gsub('___','.')})
    end
    cols
  end
  
  def your_selected_case_columns
    your_case_columns.select { |col| col[:value] == true }
  end
  
  def all_selected_case_columns
    all_case_columns.select { |col| col[:value] == true }
  end
  
  def all_case_columns
    cols = ALL_CASE_COLUMNS.dup
    cols.each do |col|
      col.merge!({:attr => 'all_'+col[:col], :value => send('all_'+col[:col]), :sort => col[:col].gsub('___','.')})
    end
    cols
  end
end
