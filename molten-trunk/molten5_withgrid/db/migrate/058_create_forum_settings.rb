class CreateForumSettings < ActiveRecord::Migration
    # old beast migration
  BEAST = true
  def self.up
    # create_table :forum_setting do |t|
    #     t.column :sfcontact_id, :string
    #     t.column :agreed_to_terms_at, :datetime
    #     t.column :name, :string
    #     t.column :created_at, :datetime
    #     t.column :updated_at, :datetime
    #   end
  end

  def self.down
    # drop_table :forum_setting
  end
end
