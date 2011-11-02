/**
 * 
 */
package org.projectsin.client.impl;

import java.util.Collection;

import org.projectsin.client.api.SinIndexable;
import org.projectsin.client.api.SinSearchQuery;
import org.projectsin.client.api.SinSearchResult;
import org.projectsin.client.api.SinStore;

/**
 * @author ruslan
 *
 */
public class SinStoreImpl implements SinStore
{

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#submit(org.projectsin.client.api.SinIndexable)
   */
  @Override
  public void submit(SinIndexable doc)
  {
    // TODO Auto-generated method stub

  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#submit(java.util.Collection)
   */
  @Override
  public void submit(Collection<SinIndexable> docs)
  {
    // TODO Auto-generated method stub

  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#update(org.projectsin.client.api.SinIndexable)
   */
  @Override
  public void update(SinIndexable doc)
  {
    // TODO Auto-generated method stub

  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#remove(long)
   */
  @Override
  public void remove(long id)
  {
    // TODO Auto-generated method stub

  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#remove(java.util.Collection)
   */
  @Override
  public void remove(Collection<Long> ids)
  {
    // TODO Auto-generated method stub

  }

  /* (non-Javadoc)
   * @see org.projectsin.client.api.SinStore#search(org.projectsin.client.api.SinSearchQuery)
   */
  @Override
  public SinSearchResult search(SinSearchQuery query)
  {
    // TODO Auto-generated method stub
    return null;
  }

}
