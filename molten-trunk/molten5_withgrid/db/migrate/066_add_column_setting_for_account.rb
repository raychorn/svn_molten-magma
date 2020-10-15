class AddColumnSettingForAccount < ActiveRecord::Migration
  def self.up
    add_column :case_columns_setting, :your_account, :boolean
    add_column :case_columns_setting, :all_account, :boolean
  end

  def self.down
    remove_column :case_columns_setting, :your_account
    remove_column :case_columns_setting, :all_account
  end
end
