class CreateCaseReports < ActiveRecord::Migration
  def self.up
    create_table :case_report do |t|
      t.string :name
      t.string :contact_id
      t.string :query
      t.datetime :created_at
      t.datetime :updated_at

      t.timestamps
    end
  end

  def self.down
    drop_table :case_report
  end
end
