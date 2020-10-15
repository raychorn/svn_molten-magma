class AddCaseReportsAccountIdForShared < ActiveRecord::Migration
  def self.up
    add_column :case_report, :account_id, :string
  end

  def self.down
    remove_column :case_report, :account_id
  end
end
