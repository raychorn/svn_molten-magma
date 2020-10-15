# In a migration, set the 'BEAST' constant to 'TRUE' if this migration should be restricted to 
# the beast database.
module ActiveRecord
  class Migration
    class << self
      def method_missing(method, *arguments, &block)
       say_with_time "#{method}(#{arguments.map { |a| a.inspect }.join(", ")})" do
         arguments[0] = Migrator.proper_table_name(arguments.first) unless arguments.empty? || method == :execute
         if (self.const_defined?('BEAST'))
           write "Using beast database for this migration: (#{Post.connection.current_database})"
           eval("Post.connection.send(method, *arguments, &block)")
         else
           ActiveRecord::Base.connection.send(method, *arguments, &block)
         end
       end
     end
   
   end
  end
end

module  ActiveRecord
  class Base
  end
end