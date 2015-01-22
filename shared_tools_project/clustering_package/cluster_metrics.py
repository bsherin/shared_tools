__author__ = 'bls910'

import numpy
import copy

from myclusterutil import normalize

distance_metric_dict = {}
cluster_metric_dict = {}

gamma = .5


def distance_metric(dm):
    """Decorator function used to register each distance metric in distance_metric_dict."""

    distance_metric_dict[dm.__name__] = dm
    return dm

def cluster_metric(cm):
    """Decorator function used to register each distance metric in distance_metric_dict."""

    cluster_metric_dict[cm.__name__] = cm
    return cm


@distance_metric
def euclidean_distance(u, v):
    """
    Returns the euclidean distance between vectors u and v. This is equivalent
    to the length of the vector (u - v).
    """
    diff = u - v
    return numpy.sqrt(numpy.dot(diff, diff))

@distance_metric
def cosine_distance(u, v):
    """
    Returns the cosine of the angle between vectors v and u. This is equal to
    u.v / |u||v|.
    """
    return numpy.dot(u, v) / (numpy.sqrt(numpy.dot(u, u)) * numpy.sqrt(numpy.dot(v, v)))

@distance_metric
def normalize_first_euclidean_disstance(u, v):
    return euclidean_distance(normalize(u), normalize(v))

def get_cluster_centroids(clustered_vectors):
    # Compute the cluster centroids
    centroids = []
    for cluster in clustered_vectors:
        centroid = numpy.array(copy.deepcopy(cluster[0]))
        for vector in cluster[1:]:
            centroid += vector
        centroid = centroid / len(cluster)
        centroids.append(centroid)
    return centroids


@cluster_metric
def compute_tss(clustered_vectors, metric=euclidean_distance):

    all_vectors = []
    for cluster in clustered_vectors:
        all_vectors += cluster

    v_tot = numpy.array(copy.deepcopy(all_vectors[0]))
    for vector in all_vectors[1:]:
        v_tot = v_tot + numpy.array(vector)

    v_avg = v_tot / len(all_vectors)
    tss = 0
    for vector in all_vectors:
        dist = metric(vector, v_avg)
        tss = tss + dist * dist
    return tss

@cluster_metric
def compute_bss_indirectly(clustered_vectors, metric=euclidean_distance):
    rss = compute_rss(clustered_vectors, metric)
    tss = compute_tss(clustered_vectors, metric)
    bss = tss - rss
    return bss

@cluster_metric
def compute_bss(clustered_vectors, metric=euclidean_distance):

    # Find the size of each cluster
    cluster_sizes = [len(cluster) for cluster in clustered_vectors]

    # Compute the cluster centroids
    centroids = get_cluster_centroids(clustered_vectors)

    # Find the average of the centroids
    avg_centroid = copy.deepcopy(centroids[0])
    for centroid in centroids[1:]:
        avg_centroid += centroid
    avg_centroid = avg_centroid / len(centroids)

    # compute the result
    bss = 0
    for i, centroid in enumerate(centroids):
        dist = metric(centroid, avg_centroid)
        bss = bss + cluster_sizes[i] * dist * dist
    return bss

@cluster_metric
def compute_rss(clustered_vectors, metric=euclidean_distance):
    rss = 0
    centroids = get_cluster_centroids(clustered_vectors)
    for i, cluster in enumerate(clustered_vectors):
        for vector in cluster:
            dist = metric(vector, centroids[i])
            rss = rss + dist * dist
    return rss

# Compute list of pseudo-fs
# pseudo-f = (BSS / (num_clusters - 1)) / (RSS / (num_observations - num_clusters)))
@cluster_metric
def compute_pseudo_f(clustered_vectors, metric=euclidean_distance):
    num_clusters = len(clustered_vectors)
    num_obs = 0
    for cluster in clustered_vectors:
        num_obs += len(cluster)
    if (num_clusters == 1) or (num_clusters == num_obs):
        return 0
    bss = compute_bss(clustered_vectors, metric)
    rss = compute_rss(clustered_vectors, metric)
    pseudo_f = (bss / (num_clusters - 1)) / (rss / (num_obs - num_clusters))
    return pseudo_f

@cluster_metric
def compute_pseudo_f_indirecly(clustered_vectors, metric=euclidean_distance):
    num_clusters = len(clustered_vectors)
    num_obs = 0
    for cluster in clustered_vectors:
        num_obs += len(cluster)
    if (num_clusters == 1) or (num_clusters == num_obs):
        return 0
    bss = compute_bss_indirectly(clustered_vectors, metric)
    rss = compute_rss(clustered_vectors, metric)
    pseudo_f = (bss / (num_clusters - 1)) / (rss / (num_obs - num_clusters))
    return pseudo_f

def average_distance_of_vector_to_set(the_v, the_set, metric=euclidean_distance):
    total_dist = 0
    for v in the_set:
        total_dist += metric(the_v, v)
    return total_dist / len(the_set)

def find_nearest_neighbor(the_v, the_set, metric=euclidean_distance):
    current_low_distance = None
    current_neighbor = None
    for i, v in enumerate(the_set):
        dist = metric(the_v, v)
        if (current_low_distance == None) or (dist < current_low_distance):
            current_low_distance = dist
            current_neighbor = i
    return current_neighbor

def get_cluster_silhouette(cluster, other_clusters, metric):
    other_centroids = get_cluster_centroids(other_clusters)
    cluster_s = 0
    for j in range(len(cluster)):
        v = cluster[j]
        the_set = cluster[:j] + cluster[j+1:]
        a = average_distance_of_vector_to_set(v, the_set, metric)
        neighbor_cluster = other_clusters[find_nearest_neighbor(v, other_centroids, metric)]
        b = average_distance_of_vector_to_set(v, neighbor_cluster, metric)
        s_score = (b - a) / max([a, b])
        cluster_s += s_score
    return cluster_s / len(cluster)

@cluster_metric
def compute_average_silhouette_score(clustered_vectors, metric=euclidean_distance):

    num_obs = 0
    if len(clustered_vectors) <= 1:
        return 0
    centroids = get_cluster_centroids(clustered_vectors)
    for cluster in clustered_vectors:
        num_obs += len(cluster)

    total_s = 0
    print "working with ", len(clustered_vectors), " clusters"
    for i in range(len(clustered_vectors)):
        cluster = clustered_vectors[i]
        # other_centroids = centroids[:i] + centroids[i+1:]
        other_clusters = clustered_vectors[:i] + clustered_vectors[i+1:]
        cluster_s = get_cluster_silhouette(cluster, other_clusters, metric)
        total_s += cluster_s * len(cluster)
        print "Silhouette for cluster ", i, cluster_s
    return total_s / num_obs

def main():
    clustered_vectors = [[numpy.array([ 0.92428227,  0.7738934 ]), numpy.array([ 0.87636597,  0.93316011])],
                         [numpy.array([ 0.19926005,  0.62370866]), numpy.array([ 0.25443179,  0.98528374])],
                         [numpy.array([ 0.97519546,  0.30069026]), numpy.array([ 0.69871358,  0.02362695])]]

    print "RSS is ", compute_rss(clustered_vectors)
    print "TSS is", compute_tss(clustered_vectors)
    print "BSS is ", compute_bss(clustered_vectors)
    print "BSS indirect is ", compute_bss_indirectly(clustered_vectors)
    print "pseudo-f is", compute_pseudo_f(clustered_vectors)
    print "pseudo-f indirect is ", compute_pseudo_f_indirecly(clustered_vectors)
    print "average silhouette is ", compute_average_silhouette_score(clustered_vectors)


if __name__ == '__main__':
    main()
