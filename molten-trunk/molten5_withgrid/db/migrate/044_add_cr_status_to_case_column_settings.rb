class AddCrStatusToCaseColumnSettings < ActiveRecord::Migration
  def self.up
    add_column :case_columns_setting, :your_cr_status__c, :boolean, :default => false
    add_column :case_columns_setting, :all_cr_status__c, :boolean, :default => false
  end

  def self.down
    remove_column :case_columns_setting, :your_cr_status__c
    remove_column :case_columns_setting, :all_cr_status__c
  end
end
