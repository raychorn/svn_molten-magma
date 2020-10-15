# Modified from Stephen F. Booth's Sorting Helper
# http://wiki.rubyonrails.org/rails/pages/Sort+Helper
module  SortHelper
  class Sorter
    def initialize(controller, columns, sort, order = 'ASC', default_sort = 'id', default_order = 'ASC')
          sort            = default_sort unless columns.include? sort
          order           = default_order unless ['ASC', 'DESC'].include? order

          @controller     = controller
          @columns        = columns
          @sort           = sort
          @order          = order
          @default_sort   = default_sort
          @default_order  = default_order
        end

        def to_sql
          @sort + ' ' + @order
        end

        def to_link(column, params={})
          column = @default_sort unless @columns.include?(column)

          if column == @sort
            order = ('ASC' == @order ? 'DESC' : 'ASC')
          else
            order = @default_order
          end

          { :params => { 'sort' => column, 'order' => order }.merge(params) }
        end # to_link    
  end # Sorter
end # SortHelper


ApplicationHelper.send(:include, SortHelper)