class AddPostCountToForumSetting < ActiveRecord::Migration
    # old beast migration
  BEAST = true
  def self.up
    # add_column :forum_setting, :posts_count, :integer, :default => 0
  end

  def self.down
    # remove_column :forum_setting, :posts_count
  end
end
