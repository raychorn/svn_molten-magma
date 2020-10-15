class CreateSfmoltenPosts < ActiveRecord::Migration
  def self.up
    create_table :sfmolten_post do |t|
      t.column :sf_id, :string
    end
  end

  def self.down
    drop_table :sfmolten_post
  end
end
