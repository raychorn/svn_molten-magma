module ActionController

  module Pagination     
      def paginate_collection(collection, options = {})
        default_options = {:per_page => 10, :page => 1}
        options = default_options.merge(options)
        total = options[:total] ? options[:total] : collection.size
        records = WillPaginate::Collection.create((options[:page]),options[:per_page]) do |pager|
          pager.replace(collection)
          pager.total_entries = total
        end
      end  
  end

end