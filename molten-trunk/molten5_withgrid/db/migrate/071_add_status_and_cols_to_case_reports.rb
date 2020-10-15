class AddStatusAndColsToCaseReports < ActiveRecord::Migration
  def self.up
    add_column :case_report, :status_array, :text
    add_column :case_report, :column_array, :text
  end

  def self.down
    remove_column :case_report, :status_array
    remove_column :case_report, :column_array
  end
end
