class AddAccountFilters < ActiveRecord::Migration
  def self.up
    add_column :case_report, :account_ids_array, :text
    add_column :sfcontact, :account_filter_ids_array, :text
  end

  def self.down
    remove_column :case_report, :account_ids_array
    remove_column :sfcontact, :account_filter_ids_array
  end
end
