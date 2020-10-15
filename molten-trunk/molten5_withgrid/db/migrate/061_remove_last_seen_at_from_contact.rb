class RemoveLastSeenAtFromContact < ActiveRecord::Migration
    # old beast migration
  def self.up
    # remove_column :sfcontact, :last_seen_at
  end

  def self.down
    # add_column :sfcontact, :last_seen_at, :datetime
  end
end
