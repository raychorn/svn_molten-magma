class AddCustomRailsCron < ActiveRecord::Migration
  def self.up
    create_table :rails_cron do |t|
      t.column :command, :text
      t.column :start, :integer
      t.column :finish, :integer
      t.column :every, :integer
    end
    
    add_column :rails_cron, :concurrent, :boolean
    # custom
    add_column :rails_cron, :interval_string, :string
  end

  def self.down
    drop_table :rails_cron
  end
end
