class CreateCaseColumnsSettings < ActiveRecord::Migration
  def self.up
    create_table :case_columns_setting do |t|
      t.column :sfcontact_setting_id, :integer
      CaseColumnsSetting::YOUR_CASE_COLUMNS.each do |col|
        t.column 'your_'+col[:col], :boolean, :default => col[:default]
      end
      CaseColumnsSetting::ALL_CASE_COLUMNS.each do |col|
       t.column 'all_'+col[:col], :boolean, :default => col[:default]
      end
    end
  end

  def self.down
    drop_table :case_columns_setting
  end
end
