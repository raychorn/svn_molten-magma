class CreateRefreshCaches < ActiveRecord::Migration
  def self.up
    create_table :refresh_cache do |t|
      t.column :refreshable_type, :string
      t.column :refreshable_id, :string
      t.column :created_at, :datetime
    end
  end

  def self.down
    drop_table :refresh_cache
  end
end
