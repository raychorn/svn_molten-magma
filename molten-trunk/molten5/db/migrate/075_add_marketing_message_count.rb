class AddMarketingMessageCount < ActiveRecord::Migration
  def self.up
    add_column :sfcontact, :marketing_message_read_count, :integer, :default => 0
  end

  def self.down
    remove_column :sfcontact, :marketing_message_read_count
  end
end
