class AdjustGroup < ActiveRecord::Migration

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
      change_column :sfgroup, col, :datetime
    end
    add_column :sfgroup, :sf_type, :string
    change_column :sfgroup, :does_send_email_to_members, :boolean
  end

  def self.down
    COLS.each do |col|
      change_column :sfgroup, col, :string
    end
    change_column :sfgroup, :does_send_email_to_members, :string
  end

end