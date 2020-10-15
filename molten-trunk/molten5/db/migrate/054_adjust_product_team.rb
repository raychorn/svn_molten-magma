class AdjustProductTeam < ActiveRecord::Migration

  COLS = [:last_modified_date, :system_modstamp, :created_date]

  def self.up
    # Update the schema (to grab new columns)
    failed = false
    begin
      SalesforceSync.update_schema
    rescue Mysql::Error
      say "Mysql Error: #{$!.message}"
    rescue LoadError
      if !failed
        failed = true
        retry
      end
    end
    COLS.each do |col|
      change_column :sfproduct_team, col, :datetime
    end
    change_column :sfproduct_team, :is_deleted, :boolean
    #change_column :sfproduct_team, :last_activity_date, :date
  end

  def self.down
    COLS.each do |col|
      change_column :sfproduct_team, col, :string
    end
    change_column :sfproduct_team, :is_deleted, :string
    #change_column :sfproduct_team, :last_activity_date, :string
  end

end
