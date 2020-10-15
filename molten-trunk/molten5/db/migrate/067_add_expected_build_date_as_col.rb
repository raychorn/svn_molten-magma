class AddExpectedBuildDateAsCol < ActiveRecord::Migration
  def self.up
    add_column :case_columns_setting, :all_expected_build_date__c, :boolean
    add_column :case_columns_setting, :your_expected_build_date__c, :boolean
  end

  def self.down
    remove_column :case_columns_setting, :all_expected_build_date__c
    remove_column :case_columns_setting, :your_expected_build_date__c
  end
end
