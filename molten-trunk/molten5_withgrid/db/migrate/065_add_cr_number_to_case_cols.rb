class AddCrNumberToCaseCols < ActiveRecord::Migration
  def self.up
    add_column :case_columns_setting, :your_cr_number__c, :boolean
    add_column :case_columns_setting, :all_cr_number__c, :boolean
  end

  def self.down
    remove_column :case_columns_setting, :your_cr_number__c
    remove_column :case_columns_setting, :all_cr_number__c
  end
end
