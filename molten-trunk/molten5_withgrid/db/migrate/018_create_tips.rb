class CreateTips < ActiveRecord::Migration
  def self.up
    create_table :tip do |t|
      t.column :title, :string
      t.column :body, :text
      t.column :created_at, :datetime
      t.column :updated_at, :datetime
      t.column :page_id, :integer
    end
  end

  def self.down
    drop_table :tip
  end
end
