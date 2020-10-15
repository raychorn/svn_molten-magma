class AddComponent < ActiveRecord::Migration
  def self.up
    create_table :sfcomponent do |t|
      t.column :sf_id, :string
    end
  end

  def self.down
    drop_table :sfcomponent
  end
end