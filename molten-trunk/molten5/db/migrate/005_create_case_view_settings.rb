class CreateCaseViewSettings < ActiveRecord::Migration
  def self.up
    create_table :case_view_setting do |t|
      t.column :sfcontact_setting_id, :string
      t.column :status, :text
      t.column :viewable, :boolean, :default => true
    end
  end

  def self.down
    drop_table :case_view_setting
  end
end
