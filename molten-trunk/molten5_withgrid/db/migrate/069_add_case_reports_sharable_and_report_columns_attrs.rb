class AddCaseReportsSharableAndReportColumnsAttrs < ActiveRecord::Migration
  def self.up
    add_column :case_report, :shared, :boolean
    add_column :case_report, :columns, :string
  end

  def self.down
    remove_column :case_report, :columns
    remove_column :case_report, :shared
  end
end
