class ModifySfmoltenPostDateColumns < ActiveRecord::Migration
  
  COLS = [:last_modified_date, :system_modstamp, :created_date]
  
  def self.up
    # Update the schema (to grab new columns)
    SalesforceSync.update_schema
    
    COLS.each do |col|
      change_column :sfmolten_post, col, :datetime
    end
  end

  def self.down
    COLS.each do |col|
      change_column :sfmolten_post, col, :varchar
    end
  end
end
