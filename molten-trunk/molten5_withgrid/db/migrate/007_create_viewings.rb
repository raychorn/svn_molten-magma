class CreateViewings < ActiveRecord::Migration
  def self.up
    create_table :viewing do |t|
      t.column :viewable_id, :string
      t.column :viewable_type, :string
      t.column :sfcontact_id, :string
      t.column :created_at, :datetime
    end
  end

  def self.down
    drop_table :viewing
  end
end
