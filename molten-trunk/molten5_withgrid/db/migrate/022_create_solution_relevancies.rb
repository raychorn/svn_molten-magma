class CreateSolutionRelevancies < ActiveRecord::Migration
  def self.up
    create_table :solution_relevancy do |t|
      t.column :rating_value_one, :integer
      t.column :rating_value_two, :integer
      t.column :rating_value_three, :integer
      t.column :rating_value_four, :integer
      t.column :view_value, :integer
    end
  end

  def self.down
    drop_table :solution_relevancy
  end
end
