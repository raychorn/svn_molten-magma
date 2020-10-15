module Admin::ContactsHelper
  # Creates a link to sort the results by the specified column.
  def link_to_sort(name,column)
    if column == @sort
      order = ('ASC' == @order ? 'DESC' : 'ASC')
    else
      order = 'ASC'
    end
    link_to(name, params.merge({:sort => column, :order => order}))
  end
end
