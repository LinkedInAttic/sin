package org.projectsin.client.api;

import java.util.Collection;

public interface SinStore
{
  /**
   * @return
   */
  public SinIndexableFactory  getIndexableFactory();
  
  /**
   * @param doc
   */
  public void submit(SinIndexable doc);
  
  /**
   * @param docs
   */
  public void submit(Collection<SinIndexable> docs);
  
  /**
   * @param doc
   */
  public void update(SinIndexable doc);
  
  /**
   * @param id
   */
  public void remove(long id);
  /**
   * @param ids
   */
  public void remove(Collection<Long> ids);
  
  /**
   * @param query
   * @return
   */
  public SinSearchResult search(SinSearchQuery query);
}
