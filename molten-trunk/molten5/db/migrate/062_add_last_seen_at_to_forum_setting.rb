class AddLastSeenAtToForumSetting < ActiveRecord::Migration
    # old beast migration
  BEAST = true
  def self.up
    # add_column :forum_setting, :last_seen_at, :datetime
    #    ForumSetting.update_all("last_seen_at = '#{Time.now.to_s(:db)}'")
  end

  def self.down
    # remove_column :forum_setting, :last_seen_at
  end
end
