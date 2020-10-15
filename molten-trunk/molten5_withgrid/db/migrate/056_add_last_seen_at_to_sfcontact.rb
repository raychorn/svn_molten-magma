class AddLastSeenAtToSfcontact < ActiveRecord::Migration
  # old beast migration
  def self.up
    # add_column :sfcontact, :last_seen_at, :datetime
  end

  def self.down
    # remove_column :sfcontact, :last_seen_at
  end
end
