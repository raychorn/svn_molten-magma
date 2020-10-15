class AddNewCaseColumns < ActiveRecord::Migration
  def self.up
    add_column :case_columns_setting, :your_expedited_priority__c, :boolean
    add_column :case_columns_setting, :your_contact_id, :boolean    
    add_column :case_columns_setting, :your_customer_tracking__c, :boolean
    add_column :case_columns_setting, :your_weekly_notes__c, :boolean

    add_column :case_columns_setting, :all_expedited_priority__c, :boolean
    add_column :case_columns_setting, :all_contact_id, :boolean    
    add_column :case_columns_setting, :all_customer_tracking__c, :boolean
    add_column :case_columns_setting, :all_weekly_notes__c, :boolean
  end

  def self.down
    remove_column :case_columns_setting, :your_expedited_priority__c
    remove_column :case_columns_setting, :your_contact_id
    remove_column :case_columns_setting, :your_customer_tracking__c
    remove_column :case_columns_setting, :your_weekly_notes__c
    
    remove_column :case_columns_setting, :all_expedited_priority__c
    remove_column :case_columns_setting, :all_contact_id
    remove_column :case_columns_setting, :all_customer_tracking__c
    remove_column :case_columns_setting, :all_weekly_notes__c
  end
end
