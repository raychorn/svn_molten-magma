class CreateSolutionSearchLogs < ActiveRecord::Migration
  def self.up
    create_table :solution_search_log do |t|
      t.column :contact_id, :integer
      t.column :term, :string
      t.column :results_count, :integer
      t.column :created_at, :datetime
    end
  end

  def self.down
    drop_table :solution_search_log
  end
end
