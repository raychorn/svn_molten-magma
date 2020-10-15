class ChangeChangeModifyDisplayToUpdated < ActiveRecord::Migration
  def self.up
    rename_column :case_columns_setting, :your_sfcase___last_modified_date, :your_sfcase___last_updated__c
    rename_column :case_columns_setting, :all_sfcase___last_modified_date, :all_sfcase___last_updated__c
  end

  def self.down
    rename_column :case_columns_setting, :your_sfcase___last_updated__c, :your_sfcase___last_modified_date
    rename_column :case_columns_setting, :all_sfcase___last_updated__c, :all_sfcase___last_modified_date
  end
end
