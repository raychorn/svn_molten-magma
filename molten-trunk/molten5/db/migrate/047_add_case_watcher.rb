class AddCaseWatcher < ActiveRecord::Migration
  def self.up
    create_table :sfcase_watcher do |t|
      t.column :sf_id, :string
    end
  end

  def self.down
    drop_table :sfcase_watcher
  end
end
