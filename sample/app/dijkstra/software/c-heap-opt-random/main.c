//------------------------------------------------------------------------------
// Dijkstra on PyCoRAM (Software)
// Copyright (C) 2013, Shinya Takamaeda-Yamazaki
// License: Apache 2.0
//------------------------------------------------------------------------------

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>

//#define __STATIC__

#define MAX_NODES (32 * 1024 * 1024)
#define MAX_PAGES (16 * 1024 * 1024)
#define PAGE_SIZE (32)

#define MAX_INT (0xffffffff)

//------------------------------------------------------------------------------
typedef struct node Node;
typedef struct page Page;
typedef struct edge Edge;
typedef unsigned int Uint;

#include "heap.h"

struct node
{
  Node* parent_node;
  Uint current_cost;
  Page* page_addr;
  Uint visited;
};

struct edge
{
  Node* next_node;
  Uint cost;
};

struct page
{
  Uint num_entries;
  Page* next_page;
  Edge edges [PAGE_SIZE];
};

//------------------------------------------------------------------------------
Uint number_of_nodes;
Uint number_of_edges;

#ifdef __STATIC__
Node node_array [MAX_NODES];
Page page_array [MAX_PAGES];
Uint id_table [MAX_NODES];
Node* node_table [MAX_NODES];
#else
Node* node_array;
Page* page_array;
Uint* id_table;  // Address -> ID
Node** addr_table;  // ID -> Address
#endif

PriorityQueue pqueue;

Uint node_index; // for node count
Uint page_index; // for edge count

//------------------------------------------------------------------------------
Uint xorshift()
{ 
  static Uint x = 123456789;
  static Uint y = 362436069;
  static Uint z = 521288629;
  static Uint w = 88675123; 
  Uint t;
  t = x ^ (x << 11);
  x = y; y = z; z = w;
  return w = (w ^ (w >> 19)) ^ (t ^ (t >> 8)); 
}

//------------------------------------------------------------------------------
Node* get_node(Uint id)
{
  return addr_table[id];
}

//------------------------------------------------------------------------------
Uint get_id(Node* node)
{
  Uint index = (Uint)((((void*) node) - ((void*) node_array))) / sizeof(Node);
  return id_table[index];
}

//------------------------------------------------------------------------------
Node* add_node(Uint id)
{
  Node* ret = get_node(id);
  if(ret == NULL){
    number_of_nodes++;
    node_array[node_index].parent_node = 0;
    node_array[node_index].current_cost = MAX_INT;
    node_array[node_index].visited = 0;
    node_array[node_index].page_addr = NULL;
    id_table[node_index] = id;
    addr_table[id] = &node_array[node_index];
    ret = &node_array[node_index];
    node_index++;
    return ret;
  }
  return ret;
}

//------------------------------------------------------------------------------
void add_edge(Uint from, Uint to, Uint cost)
{
  number_of_edges++;

  Node* f = add_node(from);
  Node* t = add_node(to);

  if(f->page_addr == NULL){
    // New page
    f->page_addr = &page_array[page_index];
    page_index++;

    f->page_addr->next_page = NULL;
    f->page_addr->num_entries = 0;
  }

  Page* p = f->page_addr;
  while(p->next_page != NULL){
    p = p->next_page;
  }
  
  if(p->num_entries < PAGE_SIZE){
    p->edges[p->num_entries].next_node = t;
    p->edges[p->num_entries].cost = cost;
    p->num_entries++;
  }else{
    // New page
    p->next_page = &page_array[page_index];
    page_index++;

    p->next_page->next_page = NULL;
    p->next_page->num_entries = 0;

    p = p->next_page;
    p->edges[p->num_entries].next_node = t;
    p->edges[p->num_entries].cost = cost;
    p->num_entries++;
  }
}

//------------------------------------------------------------------------------
void add_frontier(Node* node, Uint cost)
{
  Heapelement he;
  he.value = cost;
  he.data = node;
  enqueue(he, &pqueue);
}

//------------------------------------------------------------------------------
void update_frontiers(Node* current_node)
{
  Uint current_cost = current_node->current_cost;
  Page* page = current_node->page_addr;

  while(page != NULL){
    Uint num_next = page->num_entries;
    Uint i;

    for(i=0; i<num_next; i++){
      //printf("page[%d]\n", i);
      Uint cost = page->edges[i].cost;
      Uint new_cost = current_cost + cost;
      Node* next_node = page->edges[i].next_node;
      if(next_node->current_cost > new_cost){
        //printf("add node:%d cost:%d\n", get_id(next_node), new_cost);
        add_frontier(next_node, new_cost);
        next_node->current_cost = new_cost;
        next_node->parent_node = current_node;
      }
    }
    
    page = page->next_page;
  }
}

//------------------------------------------------------------------------------
int is_frontier_empty()
{
  return is_empty(&pqueue);
}

//------------------------------------------------------------------------------
Node* select_frontier()
{
  //printf("current size=%d\n", pqueue.size);
  Heapelement he = dequeue(&pqueue);
  Node* n = he.data;
  return n;
}

//------------------------------------------------------------------------------
Uint find_shortest_path(Uint start, Uint goal)
{
  Node* current_node = get_node(start);
  Node* goal_node = get_node(goal);
  current_node->current_cost = 0;
  add_frontier(current_node, 0);

  while(current_node != goal_node){
    if(is_frontier_empty()) return MAX_INT;
    current_node = select_frontier();
    if(current_node->visited) continue;
    current_node->visited = 1;
    //printf("current_node=%d current_cost=%d\n", current_node->id, current_node->current_cost);
    update_frontiers(current_node);
  }

  return current_node->current_cost;
}

//------------------------------------------------------------------------------
void walk_result(Uint sum_of_cost, Uint start, Uint goal)
{
  Node* c = get_node(goal);
  printf("route: \n");

  while(c != NULL){
    Uint id = get_id(c);
    printf("%d %d\n", id, c->current_cost);
    if(id == start) break;
    c = c->parent_node;
  }
  
  printf("\r\n");
  printf("cost: %d", sum_of_cost);
  printf("\r\n");
}

//------------------------------------------------------------------------------
int main(int argc, char** argv)
{

  /*
  FILE* fp = fopen(argv[3], "r");
  if(fp == NULL){
    printf("no such file\n");
    return -1;
  }
  */

  if(argc < 5){
    printf("# Usage: ./a.out start goal num_edges num_nodes\n");
    return -1;
  }

  Uint start = atoi(argv[1]);
  Uint goal = atoi(argv[2]);

  Uint nedges = atoi(argv[3]);
  Uint nnodes = atoi(argv[4]);

  /*
  Uint start, goal;
  if(fscanf(stdin, "%d %d\n", &start, &goal) != 2){
    exit(-1);    
  }
  */

  /*
  if(fscanf(fp, "%d %d\n", &number_of_nodes, &number_of_edges) != 2){
    exit(-1);
  }
  */

  /*
  if(fscanf(stdin, "%d %d\n", &number_of_nodes, &number_of_edges) != 2){
    exit(-1);
  }
  */

  /*
  if(number_of_nodes > MAX_NODES || number_of_edges > (MAX_PAGES * PAGE_SIZE)){
    printf("Graph size exceeds the maximum memory capacity.");
    return -1;
  }
  */

  number_of_nodes = 0;
  number_of_edges = 0;
  node_index = 0;
  page_index = 0;

#ifndef __STATIC__  
  node_array = (Node*) malloc(sizeof(Node) * MAX_NODES);
  if(node_array == NULL){
    printf("can allocate a memory for node_array.\n");
    exit(-1);
  }
  page_array = (Page*) malloc(sizeof(Page) * MAX_PAGES);
  if(page_array == NULL){
    printf("can allocate a memory for page_array.\n");
    exit(-1);
  }
  id_table = (Uint*) malloc(sizeof(Uint) * MAX_NODES);
  if(id_table == NULL){
    printf("can allocate a memory for id_table.\n");
    exit(-1);
  }
  addr_table = (Node**) malloc(sizeof(Node*) * MAX_NODES);
  if(addr_table == NULL){
    printf("can allocate a memory for addr_table.\n");
    exit(-1);
  }
#endif

  init_queue(&pqueue, MAX_NODES);

  Uint i;
  for(i=0; i<MAX_NODES; i++){
    id_table[i] = 0;
    addr_table[i] = NULL;
  }

  Uint from, to, cost, prob;

  //add_edge(start, goal, 0x7fffffff);

  for(from=0; from<nnodes; from++){
    for(to=0; to<nnodes; to++){
      if(from == to) continue;
      cost = 1 + (xorshift() % 10000);
      prob = xorshift() % 1000;
      if(nedges * 1000 > nnodes * nnodes * prob){
        add_edge(from, to, cost);
        //add_edge(to, from, cost); // undirected graph
      }
    }
  }

  /*
  while(fscanf(fp, "%d %d %d\n", &from, &to, &cost) == 3){
    add_edge(from, to, cost);
    //add_edge(to, from, cost); // undirected graph
  }
  */

  /*
  while(fscanf(stdin, "%d %d %d\n", &from, &to, &cost) == 3){
    add_edge(from, to, cost);
    //add_edge(to, from, cost); // undirected graph
  }
  */

  printf("start:%d goal:%d\r\n", start, goal);
  printf("num_nodes:%d num_edges:%d\r\n", number_of_nodes, number_of_edges);

  struct timeval s, e;
  gettimeofday(&s, NULL);

  Uint sum_of_cost = find_shortest_path(start, goal);

  gettimeofday(&e, NULL);
  double exec_time = (e.tv_sec - s.tv_sec) + (e.tv_usec - s.tv_usec) * 1.0E-6;

  if(sum_of_cost < MAX_INT){
    walk_result(sum_of_cost, start, goal);
  }

  printf("exectuion time=%lf\n", exec_time);

#ifndef __STATIC__  
  free(node_array);
  free(page_array);
  free(id_table);
  free(addr_table);
#endif

  return 0;
}
