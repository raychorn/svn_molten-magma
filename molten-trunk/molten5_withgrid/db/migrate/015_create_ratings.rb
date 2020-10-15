class CreateRatings < ActiveRecord::Migration
  def self.up
    create_table :rating do |t|
      t.column :one, :integer, :default => 0
      t.column :two, :integer, :default => 0
      t.column :three, :integer, :default => 0
      t.column :four, :integer, :default => 0
      t.column :sfsolution_id, :string
    end
  end

  def self.down
    drop_table :rating
  end
end
