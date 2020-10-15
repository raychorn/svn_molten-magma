class AddTagToColDisplay < ActiveRecord::Migration
  def self.up
    add_column :case_columns_setting, :your_tag__c, :boolean
    add_column :case_columns_setting, :all_tag__c, :boolean
  end

  def self.down
    remove_column :case_columns_setting, :your_tag__c
    remove_column :case_columns_setting, :all_tag__c
  end
end
