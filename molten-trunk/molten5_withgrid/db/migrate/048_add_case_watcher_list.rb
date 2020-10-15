class AddCaseWatcherList < ActiveRecord::Migration
  def self.up
    create_table :sfcase_watcher_list do |t|
      t.column :sf_id, :string
    end
  end

  def self.down
    drop_table :sfcase_watcher_list
  end
end
