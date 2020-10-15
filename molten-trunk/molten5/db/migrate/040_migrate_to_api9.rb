class MigrateToApi9 < ActiveRecord::Migration
  def self.up
    rename_column :sfcase, :is_visible_in_css, :is_visible_in_self_service
    add_column :sfcase, :account_id, :string
  end

  def self.down
    remove_column :sfcase, :account_id
    rename_column :sfcase, :is_visible_in_self_service, :is_visible_in_css
  end
end
