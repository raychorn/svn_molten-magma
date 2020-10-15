class CreatePages < ActiveRecord::Migration
  def self.up
    create_table :page do |t|
      t.column :name, :string
      t.column :controller, :string
      t.column :action, :string
      t.column :created_at, :datetime
      t.column :updated_at, :datetime
    end
  end

  def self.down
    drop_table :page
  end
end
